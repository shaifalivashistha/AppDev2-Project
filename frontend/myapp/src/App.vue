<template>
  <div id="app">
    <router-view />
  </div>
</template>

<style lang="scss">
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}

nav {
  padding: 30px;

  a {
    font-weight: bold;
    color: #46be16;

    &.router-link-exact-active {
      color: #42b983;
    }
  }
}

body {
  margin: 0;
  padding: 0;
  // background-image: url("~@/assets/img1.jpeg");cd
  background-color: rgb(56, 156, 223);
  background-size: auto;
}
</style>
