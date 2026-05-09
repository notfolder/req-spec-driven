<template>
  <v-container class="py-8" style="max-width: 680px">
    <v-card>
      <v-card-title>ユーザー登録</v-card-title>
      <v-card-text>
        <v-text-field v-model="loginId" label="ログインID" />
        <v-text-field v-model="displayName" label="表示名" />
        <v-select v-model="role" :items="roles" label="権限" />
        <v-text-field v-model="initialPassword" label="初期PW" />
        <v-alert v-if="errorMessage" type="error" variant="tonal">{{ errorMessage }}</v-alert>
      </v-card-text>
      <v-card-actions>
        <v-btn @click="goBack">一覧へ戻る</v-btn>
        <v-spacer />
        <v-btn color="primary" @click="submit">登録</v-btn>
      </v-card-actions>
    </v-card>
  </v-container>
</template>

<script setup>
/**
 * ユーザー登録画面。
 * 要件ID: RQ-FT-REGISTER-USER
 * 設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
 * 要件概要: 管理者がユーザーを手動登録できること。
 * 設計概要: ログインID・表示名・権限・初期PWを入力して登録APIへ送信する。
 * 呼び出し先設計ID: DS-FN-REGISTER-USER-FT-REGISTER-USER
 * 呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
 */

import { ref } from "vue";
import { useRouter } from "vue-router";
import { apiSend } from "../services/api.js";

const router = useRouter();

const roles = ["管理者", "一般ユーザー"];
const loginId = ref("");
const displayName = ref("");
const role = ref("一般ユーザー");
const initialPassword = ref("");
const errorMessage = ref("");

function goBack() {
  /**
   * ユーザー一覧へ戻る。
   * 要件ID: RQ-UI-USER-MANAGEMENT-SCREEN
   * 設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   * 要件概要: 一覧画面を起点に登録画面へ遷移し戻れること。
   * 設計概要: 戻る操作でユーザー一覧画面へ遷移する。
   * 呼び出し先設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   * 呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   */

  router.push("/users");
}

async function submit() {
  /**
   * ユーザー登録を実行する。
   * 要件ID: RQ-FT-REGISTER-USER
   * 設計ID: DS-FN-REGISTER-USER-FT-REGISTER-USER
   * 要件概要: 管理者がユーザーを登録できる。
   * 設計概要: フォーム入力値を登録APIへ送信する。
   * 呼び出し先設計ID: DS-FN-REGISTER-USER-FT-REGISTER-USER
   * 呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   */

  errorMessage.value = "";
  try {
    await apiSend("/api/users", "POST", {
      login_id: loginId.value,
      display_name: displayName.value,
      role: role.value,
      initial_password: initialPassword.value,
    });
    router.push("/users");
  } catch (error) {
    errorMessage.value = String(error?.message || "ユーザー登録に失敗しました");
  }
}
</script>
