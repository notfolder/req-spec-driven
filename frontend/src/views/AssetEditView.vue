<template>
  <v-container class="py-8" style="max-width: 640px">
    <v-card>
      <v-card-title>備品編集</v-card-title>
      <v-card-text>
        <v-text-field v-model="assetNumberReadonly" label="資産管理番号" readonly />
        <v-text-field v-model="assetName" label="備品名" />
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
 * 備品編集画面。
 * 要件ID: RQ-FT-UPDATE-ASSET
 * 設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
 * 要件概要: 管理者が備品名を更新できること。
 * 設計概要: 対象資産番号を固定表示し、備品名のみ更新APIへ送信する。
 * 呼び出し先設計ID: DS-FN-UPDATE-ASSET-FT-UPDATE-ASSET
 * 呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
 */

import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { apiGet, apiSend } from "../services/api.js";

const route = useRoute();
const router = useRouter();

const assetNumberReadonly = ref("");
const assetName = ref("");
const errorMessage = ref("");

function goBack() {
  /**
   * 備品一覧画面へ戻る。
   * 要件ID: RQ-UI-ASSET-LIST-MANAGEMENT-SCREEN
   * 設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   * 要件概要: 一覧画面を基点に編集画面から戻れること。
   * 設計概要: 編集完了/キャンセル時に一覧画面へ遷移する。
   * 呼び出し先設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   */

  router.push("/assets");
}

async function loadCurrentAsset() {
  /**
   * 編集対象備品の現在値を取得する。
   * 要件ID: RQ-FT-UPDATE-ASSET
   * 設計ID: DS-FN-UPDATE-ASSET-FT-UPDATE-ASSET
   * 要件概要: 更新対象の既存値を確認できること。
   * 設計概要: 一覧API結果から対象資産を抽出し、フォーム初期値に設定する。
   * 呼び出し先設計ID: DS-FN-VIEW-ASSET-LIST-FT-VIEW-ASSET-LIST
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   */

  const assetNumber = String(route.params.assetNumber || "");
  const response = await apiGet("/api/assets");
  const target = response.items.find((item) => item.asset_number === assetNumber);
  if (!target) {
    throw new Error("対象備品が見つかりません");
  }
  assetNumberReadonly.value = target.asset_number;
  assetName.value = target.asset_name;
}

async function submit() {
  /**
   * 備品更新を実行する。
   * 要件ID: RQ-FT-UPDATE-ASSET
   * 設計ID: DS-FN-UPDATE-ASSET-FT-UPDATE-ASSET
   * 要件概要: 管理者が備品情報を更新できること。
   * 設計概要: 対象資産番号の更新APIへ備品名を送信する。
   * 呼び出し先設計ID: DS-FN-UPDATE-ASSET-FT-UPDATE-ASSET
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   */

  errorMessage.value = "";
  try {
    await apiSend(`/api/assets/${assetNumberReadonly.value}`, "PUT", {
      asset_name: assetName.value,
    });
    router.push("/assets");
  } catch (error) {
    errorMessage.value = String(error?.message || "備品更新に失敗しました");
  }
}

onMounted(async () => {
  /**
   * 画面表示時に対象備品を読み込む。
   * 要件ID: RQ-FT-UPDATE-ASSET
   * 設計ID: DS-FN-UPDATE-ASSET-FT-UPDATE-ASSET
   * 要件概要: 編集画面で対象備品を特定できること。
   * 設計概要: ルートパラメータの資産番号を使って初期値を設定する。
   * 呼び出し先設計ID: DS-FN-VIEW-ASSET-LIST-FT-VIEW-ASSET-LIST
   * 呼び出し元設計ID: DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN
   */

  try {
    await loadCurrentAsset();
  } catch (error) {
    errorMessage.value = String(error?.message || "対象備品の読み込みに失敗しました");
  }
});
</script>
