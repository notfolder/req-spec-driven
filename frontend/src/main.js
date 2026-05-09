/**
 * フロントエンドエントリポイント。
 * 要件ID: RQ-UI-WEB-GUI-USE
 * 設計ID: DS-MD-WEB-GUI-USE-UI-WEB-GUI-USE
 * 要件概要: Web GUI で備品管理・貸出管理を操作できること。
 * 設計概要: Vue/Vuetifyアプリを初期化し、ルーター構成で画面遷移を提供する。
 * 呼び出し先設計ID: DS-IF-LOGIN-SCREEN-UI-LOGIN-SCREEN, DS-IF-ASSET-LIST-MANAGEMENT-SCREEN-UI-ASSET-LIST-MANAGEMENT-SCREEN, DS-IF-USER-MANAGEMENT-SCREEN-UI-USER-MANAGEMENT-SCREEN, DS-IF-CHANGE-OWN-PASSWORD-SCREEN-FT-CHANGE-OWN-PASSWORD
 * 呼び出し元設計ID: DS-MD-WEB-GUI-USE-UI-WEB-GUI-USE
 */

import { createApp } from "vue";
import { createVuetify } from "vuetify";
import * as components from "vuetify/components";
import * as directives from "vuetify/directives";
import "vuetify/styles";
import App from "./App.vue";
import router from "./router/index.js";

const vuetify = createVuetify({
  components,
  directives,
});

createApp(App).use(vuetify).use(router).mount("#app");
