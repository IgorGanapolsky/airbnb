import React from "react";
import { SafeAreaView, Text, StyleSheet } from "react-native";
import { StatusBar } from "expo-status-bar";

export default function App() {
  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.title}>React Native + Expo Template</Text>
      <Text>Start building your app in App.tsx</Text>
      <StatusBar style="auto" />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center", padding: 16 },
  title: { fontSize: 20, fontWeight: "600", marginBottom: 8 },
});
