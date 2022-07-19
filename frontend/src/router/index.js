import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "home",
      component: HomeView,
      meta: {
        breadCrumb: [
          {
            text: "대문",
          },
        ],
      },
    },
    {
      path: "/about",
      name: "about",
      component: () => import("../views/PostView.vue"),
      props: { type: "about" },
      meta: {
        breadCrumb: [
          {
            text: "대문",
            to: { name: "home" },
          },
          {
            text: "소개",
          },
        ],
      },
    },
    {
      path: "/rules",
      name: "rules",
      component: () => import("../views/PostView.vue"),
      props: { type: "rules" },
      meta: {
        breadCrumb: [
          {
            text: "대문",
            to: { name: "home" },
          },
          {
            text: "회칙",
          },
        ],
      },
    },
    {
      path: "/notices",
      name: "notices",
      component: () => import("../views/PostListView.vue"),
      props: { type: "notices" },
      meta: {
        breadCrumb: [
          {
            text: "대문",
            to: { name: "home" },
          },
          {
            text: "공지",
          },
        ],
      },
    },
    {
      path: "/notices/:no",
      name: "notice",
      component: () => import("../views/PostView.vue"),
      props: (route) => ({ type: "notices", no: Number(route.params.no) }),
      meta: {
        breadCrumb(title) {
          return [
            {
              text: "대문",
              to: { name: "home" },
            },
            {
              text: "공지",
              to: { name: "notices" },
            },
            {
              text: title,
            },
          ];
        },
      },
    },
    {
      path: "/notices/write",
      name: "writeNotice",
      component: () => import("../views/PostWriteView.vue"),
      props: { type: "notices" },
      meta: {
        breadCrumb: [
          {
            text: "대문",
            to: { name: "home" },
          },
          {
            text: "공지",
            to: { name: "notices" },
          },
          {
            text: "편집",
          },
        ],
      },
    },
    {
      path: "/about/write",
      name: "writeAbout",
      component: () => import("../views/PostWriteView.vue"),
      props: { type: "about" },
      meta: {
        breadCrumb: [
          {
            text: "대문",
            to: { name: "home" },
          },
          {
            text: "소개",
            to: { name: "about" },
          },
          {
            text: "편집",
          },
        ],
      },
    },
    {
      path: "/rules/write",
      name: "writeRules",
      component: () => import("../views/PostWriteView.vue"),
      props: { type: "rules" },
      meta: {
        breadCrumb: [
          {
            text: "대문",
            to: { name: "home" },
          },
          {
            text: "회칙",
            to: { name: "rules" },
          },
        ],
      },
    },
    {
      path: "/me",
      name: "me",
      component: () => import("../views/MeView.vue"),
    },
    {
      path: "/magazines",
      name: "magazines",
      component: () => import("../views/MagazineGridView.vue"),
      meta: {
        breadCrumb: [
          {
            text: "대문",
            to: { name: "home" },
          },
          {
            text: "문집",
          },
        ],
      },
    },
    {
      path: "/magazines/write",
      name: "magazineWrite",
      component: () => import("../views/MagazineWriteView.vue"),
      meta: {
        breadCrumb: [
          {
            text: "대문",
            to: { name: "home" },
          },
          {
            text: "문집",
            to: { name: "magazines" },
          },
        ],
      },
    },
    {
      path: "/classes/:name",
      name: "class",
      component: () => import("../views/ClassView.vue"),
      props: (route) => ({ name: route.params.name }),
    },
    {
      path: "/classes/:name/:conducted",
      name: "classRecord",
      component: () => import("../views/ClassRecordView.vue"),
      props: (route) => ({
        name: route.params.name,
        conducted: route.params.conducted,
      }),
    },
    {
      path: "/classes/:name/write",
      name: "writeClassRecord",
      component: () => import("../views/ClassRecordWriteView.vue"),
      props: (route) => ({
        name: route.params.name,
      }),
    },
    {
      path: "/admin",
      name: "admin",
      component: () => import("../views/AdminView.vue"),
      children: [
        {
          path: "club-information",
          component: () => import("../views/AdminClubInformationView.vue"),
        },
        {
          path: "classes",
          component: () => import("../views/AdminClassInformationView.vue"),
        },
        {
          path: "members",
          component: () => import("../views/AdminMemberList.vue"),
        },
      ],
    },
  ],
});

export default router;
