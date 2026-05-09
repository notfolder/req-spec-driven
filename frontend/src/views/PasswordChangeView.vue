<template>
  <v-container class="py-8" style="max-width: 680px">
    <v-card>
      <v-card-title>パスワード変更</v-card-title>
      <v-card-text>
        <v-text-field v-model="oldPassword" label="現在のPW" type="password" />
        <v-text-field v-model="newPassword" label="新しいPW" type="password" />
        <v-text-field v-model="newPasswordConfirm" label="新しいPW確認" type="password" />
        <v-alert v-if="errorMessage" type="error" variant="tonal">{{ errorMessage }}</v-alert>
      </v-card-text>
      <v-card-actions>
        <v-btn @click="goBack">一覧へ戻る</v-btn>
        <v-spacer />
        <v-btn color="primary" @click="submit">変更</v-btn>
      </v-card-actions>
    </v-card>
  </v-container>
</template>

<script setup>
/**
 * パスワード変更画面。
 * 要件ID: RQ-FT-CHANGE-OWN-PASSWORD
 * 設計ID: DS-IF-CHANGE-OWN-PASSWORD-SCREEN-FT-CHANGE-OWN-PASSWORD
 * 要件概要: 利用者自身がパスワードを変更できること。
 * 設計概要: 現在PWと新PWを入力し、変更APIを実行する。
 * 呼び出し先設計ID: DS-FN-CHANGE-OWN-PASSWORD-FT-CHANGE-OWN-PASSWORD
 * 呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN, DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
 */

import { ref } from "vue";
import { useRouter } from "vue-router";
import { apiSend } from "../services/api.js";

const router = useRouter();

const oldPassword = ref("");
const newPassword = ref("");
const newPasswordConfirm = ref("");
const errorMessage = ref("");

function goBack() {
  /**
   * 遷移元に応じて一覧画面へ戻る。
   * 要件ID: RQ-FT-CHANGE-OWN-PASSWORD
   * 設計ID: DS-IF-CHANGE-OWN-PASSWORD-SCREEN-FT-CHANGE-OWN-PASSWORD
   * 要件概要: パスワード変更後に一覧画面へ戻れること。
   * 設計概要: 管理者はユーザー一覧へ、一般ユーザーは備品一覧へ戻す。
   * 呼び出し先設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN, DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   * 呼び出し元設計ID: DS-IF-CHANGE-OWN-PASSWORD-SCREEN-FT-CHANGE-OWN-PASSWORD
   */

  if (localStorage.getItem("role") === "管理者") {
    router.push("/users");
    return;
  }
  router.push("/assets");
}

async function submit() {
  /**
   * 自己パスワード変更を実行する。
   * 要件ID: RQ-FT-CHANGE-OWN-PASSWORD
   * 設計ID: DS-FN-CHANGE-OWN-PASSWORD-FT-CHANGE-OWN-PASSWORD
   * 要件概要: 利用者が現在PWを確認して新PWへ変更できること。
   * 設計概要: 新PW確認一致を検証した上で変更APIへ送信する。
   * 呼び出し先設計ID: DS-FN-CHANGE-OWN-PASSWORD-FT-CHANGE-OWN-PASSWORD
   * 呼び出し元設計ID: DS-IF-CHANGE-OWN-PASSWORD-SCREEN-FT-CHANGE-OWN-PASSWORD
   */

  errorMessage.value = "";
  if (newPassword.value !== newPasswordConfirm.value) {
    errorMessage.value = "新しいPW確認が一致しません";
    return;
  }
  try {
    await apiSend("/api/users/me/password", "POST", {
      old_password: oldPassword.value,
      new_password: newPassword.value,
    });
    goBack();
  } catch (error) {
    errorMessage.value = String(error?.message || "パスワード変更に失敗しました");
  }
}
</script>
