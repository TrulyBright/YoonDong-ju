<script setup>
import Markdown from "vue3-markdown-it";
</script>
<script>
export default {
  props: {
    content: String,
  },
};
</script>

<template>
  <div><Markdown :source="content"></Markdown></div>
</template>
