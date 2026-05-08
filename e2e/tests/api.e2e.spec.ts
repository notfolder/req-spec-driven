import { expect, test } from '@playwright/test';

function uniqueId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.floor(Math.random() * 10000)}`;
}

test('E2E: ロール別ログイン制御', async ({ request, baseURL }) => {
  const adminId = uniqueId('admin');
  const viewerId = uniqueId('viewer');

  const createAdmin = await request.post(`${baseURL}/api/users`, {
    data: {
      login_id: adminId,
      user_name: '管理者テスト',
      password: 'Passw0rd!',
      role: 'admin',
    },
  });
  expect(createAdmin.ok()).toBeTruthy();

  const createViewer = await request.post(`${baseURL}/api/users`, {
    data: {
      login_id: viewerId,
      user_name: '一般テスト',
      password: 'Passw0rd!',
      role: 'viewer',
    },
  });
  expect(createViewer.ok()).toBeTruthy();

  const adminLogin = await request.post(`${baseURL}/api/auth/login`, {
    data: { login_id: adminId, password: 'Passw0rd!' },
  });
  expect(adminLogin.ok()).toBeTruthy();
  const adminBody = await adminLogin.json();
  expect(adminBody.can_manage).toBe(true);

  const viewerLogin = await request.post(`${baseURL}/api/auth/login`, {
    data: { login_id: viewerId, password: 'Passw0rd!' },
  });
  expect(viewerLogin.ok()).toBeTruthy();
  const viewerBody = await viewerLogin.json();
  expect(viewerBody.can_manage).toBe(false);
});

test('E2E: 備品 CRUD', async ({ request, baseURL }) => {
  const assetId = uniqueId('asset');

  const createAsset = await request.post(`${baseURL}/api/assets`, {
    data: {
      asset_id: assetId,
      asset_name: '作成テスト備品',
    },
  });
  expect(createAsset.ok()).toBeTruthy();

  const listAfterCreate = await request.get(`${baseURL}/api/assets`);
  expect(listAfterCreate.ok()).toBeTruthy();
  const createdList = await listAfterCreate.json();
  const created = createdList.find((x: { asset_id: string }) => x.asset_id === assetId);
  expect(created).toBeTruthy();
  expect(created.asset_name).toBe('作成テスト備品');

  const updateAsset = await request.put(`${baseURL}/api/assets/${assetId}`, {
    data: {
      asset_id: assetId,
      asset_name: '更新後備品名',
    },
  });
  expect(updateAsset.ok()).toBeTruthy();

  const listAfterUpdate = await request.get(`${baseURL}/api/assets`);
  expect(listAfterUpdate.ok()).toBeTruthy();
  const updatedList = await listAfterUpdate.json();
  const updated = updatedList.find((x: { asset_id: string }) => x.asset_id === assetId);
  expect(updated.asset_name).toBe('更新後備品名');

  const deleteAsset = await request.delete(`${baseURL}/api/assets/${assetId}`);
  expect(deleteAsset.ok()).toBeTruthy();

  const listAfterDelete = await request.get(`${baseURL}/api/assets`);
  expect(listAfterDelete.ok()).toBeTruthy();
  const deletedList = await listAfterDelete.json();
  const deleted = deletedList.find((x: { asset_id: string }) => x.asset_id === assetId);
  expect(deleted).toBeFalsy();
});

test('E2E: 貸出中の備品削除が拒否される', async ({ request, baseURL }) => {
  const userId = uniqueId('delete-block-user');
  const assetId = uniqueId('delete-block-asset');

  const createUser = await request.post(`${baseURL}/api/users`, {
    data: {
      login_id: userId,
      user_name: '削除禁止ユーザー',
      password: 'Passw0rd!',
      role: 'viewer',
    },
  });
  expect(createUser.ok()).toBeTruthy();

  const createAsset = await request.post(`${baseURL}/api/assets`, {
    data: {
      asset_id: assetId,
      asset_name: '削除禁止確認備品',
    },
  });
  expect(createAsset.ok()).toBeTruthy();

  const lend = await request.post(`${baseURL}/api/assets/${assetId}/lend`, {
    data: { login_id: userId },
  });
  expect(lend.ok()).toBeTruthy();

  const deleteAsset = await request.delete(`${baseURL}/api/assets/${assetId}`);
  expect(deleteAsset.status()).toBe(400);
  const deleteBody = await deleteAsset.json();
  expect(deleteBody.detail).toContain('貸出中');
});

test('E2E: 貸出と返却で状態が切り替わる', async ({ request, baseURL }) => {
  const userId = uniqueId('borrower');
  const assetId = uniqueId('lend-asset');

  const createUser = await request.post(`${baseURL}/api/users`, {
    data: {
      login_id: userId,
      user_name: '貸出対象者',
      password: 'Passw0rd!',
      role: 'viewer',
    },
  });
  expect(createUser.ok()).toBeTruthy();

  const createAsset = await request.post(`${baseURL}/api/assets`, {
    data: {
      asset_id: assetId,
      asset_name: '貸出返却テスト備品',
    },
  });
  expect(createAsset.ok()).toBeTruthy();

  const lend = await request.post(`${baseURL}/api/assets/${assetId}/lend`, {
    data: { login_id: userId },
  });
  expect(lend.ok()).toBeTruthy();

  const listAfterLend = await request.get(`${baseURL}/api/assets`);
  expect(listAfterLend.ok()).toBeTruthy();
  const lendedList = await listAfterLend.json();
  const lended = lendedList.find((x: { asset_id: string }) => x.asset_id === assetId);
  expect(lended.status).toBe('貸出中');
  expect(lended.current_user_name).toBe('貸出対象者');

  const returned = await request.post(`${baseURL}/api/assets/${assetId}/return`);
  expect(returned.ok()).toBeTruthy();

  const listAfterReturn = await request.get(`${baseURL}/api/assets`);
  expect(listAfterReturn.ok()).toBeTruthy();
  const returnedList = await listAfterReturn.json();
  const returnedAsset = returnedList.find((x: { asset_id: string }) => x.asset_id === assetId);
  expect(returnedAsset.status).toBe('貸出可能');
  expect(returnedAsset.current_user_name).toBe('');
});

test('E2E: 貸出中備品への再貸出が拒否される', async ({ request, baseURL }) => {
  const firstUserId = uniqueId('relend-first');
  const secondUserId = uniqueId('relend-second');
  const assetId = uniqueId('relend-asset');

  const createFirstUser = await request.post(`${baseURL}/api/users`, {
    data: {
      login_id: firstUserId,
      user_name: '最初の利用者',
      password: 'Passw0rd!',
      role: 'viewer',
    },
  });
  expect(createFirstUser.ok()).toBeTruthy();

  const createSecondUser = await request.post(`${baseURL}/api/users`, {
    data: {
      login_id: secondUserId,
      user_name: '再貸出利用者',
      password: 'Passw0rd!',
      role: 'viewer',
    },
  });
  expect(createSecondUser.ok()).toBeTruthy();

  const createAsset = await request.post(`${baseURL}/api/assets`, {
    data: {
      asset_id: assetId,
      asset_name: '再貸出拒否確認備品',
    },
  });
  expect(createAsset.ok()).toBeTruthy();

  const firstLend = await request.post(`${baseURL}/api/assets/${assetId}/lend`, {
    data: { login_id: firstUserId },
  });
  expect(firstLend.ok()).toBeTruthy();

  const secondLend = await request.post(`${baseURL}/api/assets/${assetId}/lend`, {
    data: { login_id: secondUserId },
  });
  expect(secondLend.status()).toBe(400);
  const secondLendBody = await secondLend.json();
  expect(secondLendBody.detail).toContain('貸出中');
});

test('E2E: 一般利用者向け貸出可能一覧表示', async ({ request, baseURL }) => {
  const userId = uniqueId('viewer-login');
  const availableAssetId = uniqueId('available-asset');
  const borrowedAssetId = uniqueId('borrowed-asset');

  const createViewer = await request.post(`${baseURL}/api/users`, {
    data: {
      login_id: userId,
      user_name: '閲覧ユーザー',
      password: 'Passw0rd!',
      role: 'viewer',
    },
  });
  expect(createViewer.ok()).toBeTruthy();

  const createAvailableAsset = await request.post(`${baseURL}/api/assets`, {
    data: {
      asset_id: availableAssetId,
      asset_name: '貸出可能備品',
    },
  });
  expect(createAvailableAsset.ok()).toBeTruthy();

  const createBorrowedAsset = await request.post(`${baseURL}/api/assets`, {
    data: {
      asset_id: borrowedAssetId,
      asset_name: '貸出中備品',
    },
  });
  expect(createBorrowedAsset.ok()).toBeTruthy();

  const lend = await request.post(`${baseURL}/api/assets/${borrowedAssetId}/lend`, {
    data: { login_id: userId },
  });
  expect(lend.ok()).toBeTruthy();

  const availability = await request.get(`${baseURL}/api/assets/availability`);
  expect(availability.ok()).toBeTruthy();
  const rows = await availability.json();

  const available = rows.find((x: { asset_id: string }) => x.asset_id === availableAssetId);
  const borrowed = rows.find((x: { asset_id: string }) => x.asset_id === borrowedAssetId);

  expect(available.status).toBe('貸出可能');
  expect(available.current_user_name).toBe('');
  expect(borrowed.status).toBe('貸出中');
  expect(borrowed.current_user_name).toBe('閲覧ユーザー');
});

test('E2E: 一覧取得失敗時にエラーを検知する', async ({ request, baseURL }) => {
  const invalidEndpoint = await request.get(`${baseURL}/api/assets/availability-invalid`);
  expect(invalidEndpoint.status()).toBe(405);
});
