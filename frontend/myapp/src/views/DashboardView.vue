<template>
  <div id="dashboard">
    <DashboardPage></DashboardPage>
  </div>
</template>
<script>
import DashboardPage from "@/components/DashboardPage.vue";

export default {
  name: "DashboardView",
  components: {
    DashboardPage,
  },
};
</script>
<style>
h1 {
  text-align: center;
}
</style>
