<template>
  <v-app-bar color="blue-grey-darken-2" density="comfortable" dark>
    <v-toolbar-title>{{ title }}</v-toolbar-title>
    <v-spacer />
    <v-btn
      v-if="showAssetList"
      variant="tonal"
      class="mx-1"
      @click="$router.push('/assets')"
    >
      備品一覧へ
    </v-btn>
    <v-btn
      v-if="showAssetCreate"
      variant="tonal"
      class="mx-1"
      @click="$router.push('/assets/new')"
    >
      備品登録画面へ
    </v-btn>
    <v-btn
      v-if="showUserList"
      variant="tonal"
      class="mx-1"
      @click="$router.push('/users')"
    >
      ユーザー一覧へ
    </v-btn>
    <v-btn
      v-if="showUserCreate"
      variant="tonal"
      class="mx-1"
      @click="$router.push('/users/new')"
    >
      ユーザー登録画面へ
    </v-btn>
    <v-btn
      v-if="showPasswordReset"
      variant="tonal"
      class="mx-1"
      @click="emitPasswordReset"
    >
      初期PW再設定
    </v-btn>
    <v-btn
      v-if="showPasswordChange"
      variant="tonal"
      class="mx-1"
      @click="$router.push('/password/change')"
    >
      パスワード変更へ
    </v-btn>
    <v-btn variant="outlined" class="mx-1" @click="logout">
      ログアウト
    </v-btn>
  </v-app-bar>
</template>

<script setup>
/**
 * 一覧画面で共通利用するヘッダーナビゲーション。
 * 要件ID: RQ-FT-AUTHORIZE-BY-ROLE
 * 設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
 * 要件概要: ロールに応じて利用可能な操作を制御する。
 * 設計概要: 画面最上部にナビゲーションを固定し、表示条件に応じてボタンを表示する。
 * 呼び出し先設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN, DS-IF-CHANGE-OWN-PASSWORD-SCREEN-FT-CHANGE-OWN-PASSWORD, DS-FN-AUTHORIZE-BY-ROLE-FT-AUTHORIZE-BY-ROLE
 * 呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN, DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
 */

import { computed } from "vue";
import { useRouter } from "vue-router";

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  mode: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(["password-reset"]);

const router = useRouter();

const isAdmin = computed(() => localStorage.getItem("role") === "管理者");

const showAssetList = computed(() => props.mode === "users" && isAdmin.value);
const showAssetCreate = computed(() => props.mode === "assets" && isAdmin.value);
const showUserList = computed(() => props.mode === "assets" && isAdmin.value);
const showUserCreate = computed(() => props.mode === "users" && isAdmin.value);
const showPasswordReset = computed(() => props.mode === "users" && isAdmin.value);
const showPasswordChange = computed(() => props.mode === "assets" || props.mode === "users");

function emitPasswordReset() {
  /**
   * 初期PW再設定イベントを親へ通知する。
   * 要件ID: RQ-FT-RESET-USER-PASSWORD
   * 設計ID: DS-FN-RESET-USER-PASSWORD-FT-RESET-USER-PASSWORD
   * 要件概要: 管理者が初期PW再設定を実行できること。
   * 設計概要: ナビゲーションボタン押下で再設定ダイアログ表示をトリガーする。
   * 呼び出し先設計ID: DS-FN-RESET-USER-PASSWORD-FT-RESET-USER-PASSWORD
   * 呼び出し元設計ID: DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   */

  emit("password-reset");
}

function logout() {
  /**
   * ログアウトしてログイン画面へ戻る。
   * 要件ID: RQ-FT-AUTHENTICATE-USER
   * 設計ID: DS-FN-AUTHENTICATE-USER-FT-AUTHENTICATE-USER
   * 要件概要: 認証状態に基づいて画面利用を制御する。
   * 設計概要: セッション情報を削除し、未認証状態へ遷移させる。
   * 呼び出し先設計ID: DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN, DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN
   */

  localStorage.removeItem("token");
  localStorage.removeItem("role");
  localStorage.removeItem("login_id");
  localStorage.removeItem("display_name");
  router.push("/");
}
</script>
