import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";
import AccountDetailsView from "../views/AccountDetailsView.vue";
import AccountsView from "../views/AccountsView.vue";

const routes: Array<RouteRecordRaw> = [
  {
    path: "/",
    redirect: "/accounts",
  },
  {
    path: "/accounts",
    name: "accounts",
    component: AccountsView,
  },
  {
    path: "/account-details/:id",
    name: "account-details",
    component: AccountDetailsView,
  },
  {
    path: "/about",
    name: "about",
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () =>
      import(/* webpackChunkName: "about" */ "../views/AboutView.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;
