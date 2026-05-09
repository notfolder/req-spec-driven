<template>
  <v-container class="py-8" style="max-width: 640px">
    <v-card>
      <v-card-title>備品登録</v-card-title>
      <v-card-text>
        <v-text-field v-model="assetNumber" label="資産管理番号" />
        <v-text-field v-model="assetName" label="備品名" />
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
 * 備品登録画面。
 * 要件ID: RQ-FT-REGISTER-ASSET
 * 設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
 * 要件概要: 管理者が資産管理番号と備品名を登録できること。
 * 設計概要: 登録フォーム入力を備品登録APIへ送信し、成功時に一覧へ戻る。
 * 呼び出し先設計ID: DS-FN-REGISTER-ASSET-FT-REGISTER-ASSET
 * 呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
 */

import { ref } from "vue";
import { useRouter } from "vue-router";
import { apiSend } from "../services/api.js";

const router = useRouter();
const assetNumber = ref("");
const assetName = ref("");
const errorMessage = ref("");

function goBack() {
  /**
   * 備品一覧画面へ戻る。
   * 要件ID: RQ-UI-ASSET-LIST-MANAGEMENT-SCREEN
   * 設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   * 要件概要: 一覧画面を基点に登録・編集画面へ遷移できること。
   * 設計概要: 戻る操作で備品一覧ルートへ遷移する。
   * 呼び出し先設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   */

  router.push("/assets");
}

async function submit() {
  /**
   * 備品登録を実行する。
   * 要件ID: RQ-FT-REGISTER-ASSET
   * 設計ID: DS-FN-REGISTER-ASSET-FT-REGISTER-ASSET
   * 要件概要: 管理者が備品を登録できること。
   * 設計概要: 入力値を登録APIへ送信し、成功時に備品一覧へ遷移する。
   * 呼び出し先設計ID: DS-FN-REGISTER-ASSET-FT-REGISTER-ASSET
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   */

  errorMessage.value = "";
  try {
    await apiSend("/api/assets", "POST", {
      asset_number: assetNumber.value,
      asset_name: assetName.value,
    });
    router.push("/assets");
  } catch (error) {
    errorMessage.value = String(error?.message || "備品登録に失敗しました");
  }
}
</script>
