/**
 * API呼び出しユーティリティ。
 * 要件ID: RQ-FT-AUTHENTICATE-USER
 * 設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER
 * 要件概要: 認証情報を使ってAPIを安全に呼び出せること。
 * 設計概要: `/api/` 配下へのHTTPアクセスと認証ヘッダー付与を共通化する。
 * 呼び出し先設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER, DS-FN-AUTHORIZE-BY-ROLE-FT-AUTHORIZE-BY-ROLE
 * 呼び出し元設計ID: DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN, DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN, DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN, DS-IF-CHANGE-OWN-PASSWORD-SCREEN-FT-CHANGE-OWN-PASSWORD
 */

function getAuthHeaders() {
  /**
   * ローカルストレージのトークンから認証ヘッダーを生成する。
   * 要件ID: RQ-FT-AUTHENTICATE-USER
   * 設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER
   * 要件概要: 認証済みユーザーのみ操作可能にする。
   * 設計概要: BearerトークンをAuthorizationヘッダーに設定する。
   * 呼び出し先設計ID: なし
   * 呼び出し元設計ID: DS-FN-AUTHORIZE-BY-ROLE-FT-AUTHORIZE-BY-ROLE
   */

  const token = localStorage.getItem("token") || "";
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function apiGet(path) {
  /**
   * GETリクエストを送信する。
   * 要件ID: RQ-FT-VIEW-ASSET-LIST
   * 設計ID: DS-FN-VIEW-ASSET-LIST-FT-VIEW-ASSET-LIST
   * 要件概要: 一覧取得系の参照操作を提供する。
   * 設計概要: 共通GET処理としてヘッダー付与とレスポンス変換を行う。
   * 呼び出し先設計ID: DS-FN-AUTHORIZE-BY-ROLE-FT-AUTHORIZE-BY-ROLE
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN, DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   */

  const response = await fetch(path, {
    method: "GET",
    headers: {
      ...getAuthHeaders(),
    },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "GET request failed");
  }
  return response.json();
}

export async function apiSend(path, method, payload) {
  /**
   * POST/PUT/DELETEリクエストを送信する。
   * 要件ID: RQ-FT-REGISTER-ASSET
   * 設計ID: DS-FN-REGISTER-ASSET-FT-REGISTER-ASSET
   * 要件概要: 登録・更新・削除・状態変更操作を提供する。
   * 設計概要: 共通送信処理としてJSON化、認証ヘッダー付与、エラー検知を行う。
   * 呼び出し先設計ID: DS-FN-AUTHORIZE-BY-ROLE-FT-AUTHORIZE-BY-ROLE
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN, DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN, DS-IF-CHANGE-OWN-PASSWORD-SCREEN-FT-CHANGE-OWN-PASSWORD
   */

  const response = await fetch(path, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: payload ? JSON.stringify(payload) : undefined,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `${method} request failed`);
  }
  return response.json();
}
