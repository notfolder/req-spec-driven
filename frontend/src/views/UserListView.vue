<template>
  <v-layout>
    <main-navigation-bar title="ユーザー一覧" mode="users" @password-reset="openResetDialog" />
    <v-main>
      <v-container class="py-6">
        <v-alert v-if="errorMessage" type="error" variant="tonal" class="mb-4">
          {{ errorMessage }}
        </v-alert>
        <v-card>
          <v-card-title class="text-h6">ユーザー一覧</v-card-title>
          <v-data-table
            :headers="headers"
            :items="users"
            item-key="login_id"
            :items-per-page="200"
          >
            <template #item.actions="{ item }">
              <v-btn size="small" class="mx-1" @click="goEdit(item.login_id)">編集</v-btn>
              <v-btn size="small" class="mx-1" color="error" @click="removeUser(item.login_id)">削除</v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-container>
    </v-main>
  </v-layout>

  <v-dialog v-model="resetDialog" max-width="520">
    <v-card>
      <v-card-title>初期PW再設定</v-card-title>
      <v-card-text>
        <v-select
          v-model="resetTargetLoginId"
          :items="users"
          item-title="display_name"
          item-value="login_id"
          label="対象ユーザー"
        />
        <v-text-field v-model="resetPassword" label="初期PW" />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn @click="resetDialog = false">キャンセル</v-btn>
        <v-btn color="primary" @click="resetUserPassword">再設定</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
/**
 * ユーザー一覧画面。
 * 要件ID: RQ-UI-USER-MANAGEMENT-SCREEN
 * 設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
 * 要件概要: ユーザー一覧の閲覧と行末操作（編集・削除）を提供する。
 * 設計概要: 管理者向けに一覧表示と行末ボタン、初期PW再設定導線を提供する。
 * 呼び出し先設計ID: DS-FN-REGISTER-USER-FT-REGISTER-USER, DS-FN-DELETE-USER-WITH-LOAN-CHECK-FT-DELETE-USER-WITH-LOAN-CHECK, DS-FN-RESET-USER-PASSWORD-FT-RESET-USER-PASSWORD
 * 呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
 */

import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import MainNavigationBar from "../components/MainNavigationBar.vue";
import { apiGet, apiSend } from "../services/api.js";

const router = useRouter();

const users = ref([]);
const errorMessage = ref("");
const resetDialog = ref(false);
const resetTargetLoginId = ref("");
const resetPassword = ref("");

const headers = [
  { title: "ログインID", key: "login_id" },
  { title: "表示名", key: "display_name" },
  { title: "権限", key: "role" },
  { title: "操作", key: "actions", sortable: false },
];

function ensureAdmin() {
  /**
   * 管理者権限を検証する。
   * 要件ID: RQ-FT-AUTHORIZE-BY-ROLE
   * 設計ID: DS-FN-AUTHORIZE-BY-ROLE-FT-AUTHORIZE-BY-ROLE
   * 要件概要: 一般ユーザーは管理画面へアクセスできない。
   * 設計概要: ロールが管理者でない場合に備品一覧へ戻す。
   * 呼び出し先設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   * 呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   */

  if (localStorage.getItem("role") !== "管理者") {
    router.push("/assets");
  }
}

async function loadUsers() {
  /**
   * ユーザー一覧を取得する。
   * 要件ID: RQ-FT-REGISTER-USER
   * 設計ID: DS-FN-REGISTER-USER-FT-REGISTER-USER
   * 要件概要: 管理者が登録済みユーザーを確認できること。
   * 設計概要: `/api/users` から一覧を取得し、表に表示する。
   * 呼び出し先設計ID: DS-FN-REGISTER-USER-FT-REGISTER-USER
   * 呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   */

  const response = await apiGet("/api/users");
  users.value = response.items;
}

function goEdit(loginId) {
  /**
   * ユーザー編集画面へ遷移する。
   * 要件ID: RQ-FT-UPDATE-USER
   * 設計ID: DS-FN-UPDATE-USER-FT-UPDATE-USER
   * 要件概要: 管理者がユーザー情報を編集できる。
   * 設計概要: 行末編集ボタン押下で対象ユーザーの編集画面へ遷移する。
   * 呼び出し先設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   * 呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   */

  router.push(`/users/${loginId}/edit`);
}

async function removeUser(loginId) {
  /**
   * ユーザー削除を実行する。
   * 要件ID: RQ-FT-DELETE-USER-WITH-LOAN-CHECK
   * 設計ID: DS-FN-DELETE-USER-WITH-LOAN-CHECK-FT-DELETE-USER-WITH-LOAN-CHECK
   * 要件概要: 貸出中備品保有ユーザーを削除不可とする。
   * 設計概要: 行末削除ボタン押下で削除APIを実行し、失敗時はエラー表示する。
   * 呼び出し先設計ID: DS-FN-DELETE-USER-WITH-LOAN-CHECK-FT-DELETE-USER-WITH-LOAN-CHECK
   * 呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   */

  try {
    await apiSend(`/api/users/${loginId}`, "DELETE");
    await loadUsers();
  } catch (error) {
    errorMessage.value = String(error?.message || "ユーザー削除に失敗しました");
  }
}

function openResetDialog() {
  /**
   * 初期PW再設定ダイアログを開く。
   * 要件ID: RQ-FT-RESET-USER-PASSWORD
   * 設計ID: DS-FN-RESET-USER-PASSWORD-FT-RESET-USER-PASSWORD
   * 要件概要: 管理者が初期PW再設定を実行できる。
   * 設計概要: ナビボタン押下で再設定ダイアログを表示する。
   * 呼び出し先設計ID: DS-FN-RESET-USER-PASSWORD-FT-RESET-USER-PASSWORD
   * 呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   */

  resetDialog.value = true;
}

async function resetUserPassword() {
  /**
   * 初期PW再設定を実行する。
   * 要件ID: RQ-FT-RESET-USER-PASSWORD
   * 設計ID: DS-FN-RESET-USER-PASSWORD-FT-RESET-USER-PASSWORD
   * 要件概要: 管理者が対象ユーザーの初期PWを再設定できる。
   * 設計概要: ダイアログ入力値を再設定APIへ送信する。
   * 呼び出し先設計ID: DS-FN-RESET-USER-PASSWORD-FT-RESET-USER-PASSWORD
   * 呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   */

  try {
    await apiSend(`/api/users/${resetTargetLoginId.value}/reset-password`, "POST", {
      initial_password: resetPassword.value,
    });
    resetDialog.value = false;
    resetPassword.value = "";
  } catch (error) {
    errorMessage.value = String(error?.message || "初期PW再設定に失敗しました");
  }
}

onMounted(async () => {
  /**
   * 画面初期表示時に一覧を読み込む。
   * 要件ID: RQ-UI-USER-MANAGEMENT-SCREEN
   * 設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   * 要件概要: 管理者がユーザー一覧画面を利用できること。
   * 設計概要: 権限確認後にユーザー一覧を取得する。
   * 呼び出し先設計ID: DS-FN-AUTHORIZE-BY-ROLE-FT-AUTHORIZE-BY-ROLE, DS-FN-REGISTER-USER-FT-REGISTER-USER
   * 呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   */

  ensureAdmin();
  try {
    await loadUsers();
  } catch (error) {
    errorMessage.value = String(error?.message || "ユーザー一覧取得に失敗しました");
  }
});
</script>
