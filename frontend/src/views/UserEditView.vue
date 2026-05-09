<template>
  <v-container class="py-8" style="max-width: 680px">
    <v-card>
      <v-card-title>ユーザー編集</v-card-title>
      <v-card-text>
        <v-text-field v-model="loginIdReadonly" label="ログインID" readonly />
        <v-text-field v-model="displayName" label="表示名" />
        <v-select v-model="role" :items="roles" label="権限" />
        <v-alert v-if="errorMessage" type="error" variant="tonal">{{ errorMessage }}</v-alert>
      </v-card-text>
      <v-card-actions>
        <v-btn @click="goBack">一覧へ戻る</v-btn>
        <v-spacer />
        <v-btn color="primary" @click="submit">更新</v-btn>
      </v-card-actions>
    </v-card>
  </v-container>
</template>

<script setup>
/**
 * ユーザー編集画面。
 * 要件ID: RQ-FT-UPDATE-USER
 * 設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
 * 要件概要: 管理者がユーザー情報を編集できること。
 * 設計概要: ログインIDを固定表示し、表示名と権限を更新する。
 * 呼び出し先設計ID: DS-FN-UPDATE-USER-FT-UPDATE-USER
 * 呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
 */

import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { apiGet, apiSend } from "../services/api.js";

const route = useRoute();
const router = useRouter();

const roles = ["管理者", "一般ユーザー"];
const loginIdReadonly = ref("");
const displayName = ref("");
const role = ref("一般ユーザー");
const errorMessage = ref("");

function goBack() {
  /**
   * ユーザー一覧へ戻る。
   * 要件ID: RQ-UI-USER-MANAGEMENT-SCREEN
   * 設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   * 要件概要: 編集画面から一覧へ戻れること。
   * 設計概要: 画面遷移をユーザー一覧へ固定する。
   * 呼び出し先設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   * 呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   */

  router.push("/users");
}

async function loadCurrentUser() {
  /**
   * 編集対象ユーザーの現在値を読み込む。
   * 要件ID: RQ-FT-UPDATE-USER
   * 設計ID: DS-FN-UPDATE-USER-FT-UPDATE-USER
   * 要件概要: 編集対象の現在情報を確認できること。
   * 設計概要: ユーザー一覧結果から対象ログインIDを抽出し、フォームに反映する。
   * 呼び出し先設計ID: DS-FN-REGISTER-USER-FT-REGISTER-USER
   * 呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   */

  const loginId = String(route.params.loginId || "");
  const response = await apiGet("/api/users");
  const target = response.items.find((item) => item.login_id === loginId);
  if (!target) {
    throw new Error("対象ユーザーが見つかりません");
  }
  loginIdReadonly.value = target.login_id;
  displayName.value = target.display_name;
  role.value = target.role;
}

async function submit() {
  /**
   * ユーザー更新を実行する。
   * 要件ID: RQ-FT-UPDATE-USER
   * 設計ID: DS-FN-UPDATE-USER-FT-UPDATE-USER
   * 要件概要: 表示名と権限を更新できること。
   * 設計概要: 編集APIへ更新値を送信し、成功時に一覧へ戻る。
   * 呼び出し先設計ID: DS-FN-UPDATE-USER-FT-UPDATE-USER
   * 呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   */

  errorMessage.value = "";
  try {
    await apiSend(`/api/users/${loginIdReadonly.value}`, "PUT", {
      display_name: displayName.value,
      role: role.value,
    });
    router.push("/users");
  } catch (error) {
    errorMessage.value = String(error?.message || "ユーザー更新に失敗しました");
  }
}

onMounted(async () => {
  /**
   * 画面初期化時に対象ユーザーをロードする。
   * 要件ID: RQ-FT-UPDATE-USER
   * 設計ID: DS-FN-UPDATE-USER-FT-UPDATE-USER
   * 要件概要: 編集時に対象ユーザーを特定できること。
   * 設計概要: ルートパラメータのログインIDに一致するユーザーを取得する。
   * 呼び出し先設計ID: DS-FN-REGISTER-USER-FT-REGISTER-USER
   * 呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   */

  try {
    await loadCurrentUser();
  } catch (error) {
    errorMessage.value = String(error?.message || "ユーザー読み込みに失敗しました");
  }
});
</script>
