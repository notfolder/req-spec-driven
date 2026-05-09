<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="5" lg="4">
        <v-card>
          <v-card-title class="text-h5">ログイン</v-card-title>
          <v-card-text>
            <v-text-field v-model="loginId" name="login_id" label="ログインID" />
            <v-text-field v-model="password" name="password" label="パスワード" type="password" />
            <v-alert v-if="errorMessage" type="error" variant="tonal" class="mt-2">
              {{ errorMessage }}
            </v-alert>
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn color="primary" @click="submitLogin">ログイン</v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
/**
 * ログイン画面。
 * 要件ID: RQ-UI-LOGIN-SCREEN
 * 設計ID: DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN
 * 要件概要: ログインIDとパスワードで認証を実行できる画面を提供する。
 * 設計概要: 認証APIに入力値を送信し、成功時に備品一覧画面へ遷移する。
 * 呼び出し先設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER
 * 呼び出し元設計ID: DS-MD-WEB-GUI-USE-UI-WEB-GUI-USE
 */

import { ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const loginId = ref("");
const password = ref("");
const errorMessage = ref("");

async function submitLogin() {
  /**
   * 認証APIを呼び出してログインする。
   * 要件ID: RQ-FT-AUTHENTICATE-USER
   * 設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER
   * 要件概要: 正しい認証情報の場合のみログインを許可する。
   * 設計概要: `/api/auth/login` へPOSTし、成功時にトークンを保持して遷移する。
   * 呼び出し先設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER
   * 呼び出し元設計ID: DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN
   */

  errorMessage.value = "";
  try {
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        login_id: loginId.value,
        password: password.value,
      }),
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || "ログインに失敗しました");
    }
    const data = await response.json();
    localStorage.setItem("token", data.token);
    localStorage.setItem("role", data.role);
    localStorage.setItem("login_id", data.login_id);
    localStorage.setItem("display_name", data.display_name);
    router.push("/assets");
  } catch (error) {
    errorMessage.value = String(error?.message || "ログインに失敗しました");
  }
}
</script>
