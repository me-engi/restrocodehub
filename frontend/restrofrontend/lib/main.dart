import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:get_storage/get_storage.dart';

import 'app/routes/app_pages.dart';
import 'app/app_binding.dart'; // Import your global AppBinding

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await GetStorage.init(); // Initialize GetStorage for synchronous use later

  // No need to determine initialRoute here if MyApp handles GetMaterialApp's initialRoute
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return GetMaterialApp(
      title: "Culinary AI Concierge",
      initialRoute: AppPages.INITIAL, // Start with the Splash screen route
      getPages: AppPages.routes,
      initialBinding: AppBinding(), // Load global dependencies first
      debugShowCheckedModeBanner: false, // Set to true if you want the debug banner
      theme: ThemeData(
        // primarySwatch: Colors.teal, // primarySwatch is less used with ColorScheme
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.teal,
          // You can customize other colors of the scheme here if needed:
          // primary: Colors.teal,
          // secondary: Colors.amber,
          // background: Colors.white,
          // surface: Colors.grey[50],
          // error: Colors.red,
        ),
        useMaterial3: true, // Enable Material 3 theming

        // Consistent Input Decoration Theme
        inputDecorationTheme: InputDecorationTheme(
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12.0), // Slightly more rounded
            borderSide: BorderSide(color: Colors.grey.shade400),
          ),
          enabledBorder: OutlineInputBorder( // Border when not focused
            borderRadius: BorderRadius.circular(12.0),
            borderSide: BorderSide(color: Colors.grey.shade400),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12.0),
            borderSide: BorderSide(color: Get.theme.colorScheme.primary, width: 2.0), // Use primary from ColorScheme
          ),
          labelStyle: TextStyle(color: Colors.grey.shade700),
          floatingLabelStyle: TextStyle(color: Get.theme.colorScheme.primary),
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        ),

        // Consistent ElevatedButton Theme
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: Get.theme.colorScheme.primary, // Use primary from ColorScheme
            foregroundColor: Get.theme.colorScheme.onPrimary, // Text color on primary
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
            textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, letterSpacing: 0.5),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12.0), // Consistent rounding
            ),
            elevation: 2,
          ),
        ),

        // Consistent TextButton Theme
        textButtonTheme: TextButtonThemeData(
          style: TextButton.styleFrom(
            foregroundColor: Get.theme.colorScheme.primary, // Text color
            textStyle: const TextStyle(fontWeight: FontWeight.w600),
          )
        ),

        // Consistent AppBar Theme
        appBarTheme: AppBarTheme(
          backgroundColor: Get.theme.colorScheme.surface, // Or primary for a colored AppBar
          foregroundColor: Get.theme.colorScheme.onSurface, // Text/icon color on surface
          elevation: 1, // Subtle shadow
          titleTextStyle: TextStyle(
            color: Get.theme.colorScheme.onSurface,
            fontSize: 20,
            fontWeight: FontWeight.w600,
          ),
          iconTheme: IconThemeData(color: Get.theme.colorScheme.onSurface),
        ),

        // Consistent Card Theme
        cardTheme: CardTheme(
          elevation: 2,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12.0), // Consistent rounding
          ),
          margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
        ),

        // Define other theme properties: textTheme, etc.
        textTheme: TextTheme(
          // Define headline, title, body styles etc.
          // Example:
          headlineSmall: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Get.theme.colorScheme.onSurface),
          titleLarge: TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: Get.theme.colorScheme.onSurface),
          bodyMedium: TextStyle(fontSize: 14, color: Get.theme.colorScheme.onSurface.withOpacity(0.8)),
          labelLarge: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: Colors.white), // For button text if needed
        ),
      ),
      // You can also define darkTheme: ThemeData.dark().copyWith(...)
      // darkTheme: ThemeData(
      //   colorScheme: ColorScheme.fromSeed(
      //     seedColor: Colors.teal,
      //     brightness: Brightness.dark,
      //     // Define dark theme specific colors
      //   ),
      //   useMaterial3: true,
      //   // ... other dark theme properties ...
      // ),
      // themeMode: ThemeMode.system, // Or ThemeMode.light, ThemeMode.dark
    );
  }
}