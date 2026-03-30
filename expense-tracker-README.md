# Expense Tracker (Android)

Simple personal expense tracker for Android.

## Features
- Add expense: amount, category, date, notes
- View expenses in a scrollable list
- See total expenses (overall and per-day if filtered)
- Delete expense by tapping the item
- Material 3 UI (light mode)

## Tech Stack
- Kotlin + Jetpack Compose
- Room (SQLite) for local storage
- ViewModel + StateFlow
- Material 3

## Prerequisites
- Android Studio (Arctic Fox or later)
- JDK 17
- Android SDK API 34

## Build & Run
1. Open this folder in Android Studio
2. Let Gradle sync (it will download dependencies)
3. Connect an Android device or start an emulator (API 24+)
4. Click Run (green play button)
5. The app will install and launch

## Project Structure
```
app/
 └─ src/main/
     ├─ AndroidManifest.xml
     ├─ java/com/haresh/expensetracker/
     │   ├─ MainActivity.kt (UI)
     │   ├─ data/
     │   │   ├─ Expense.kt (entity)
     │   │   ├─ ExpenseDao.kt
     │   │   ├─ AppDatabase.kt
     │   │   └─ ExpenseRepository.kt
     │   └─ ui/
     │       ├─ ExpenseViewModel.kt
     │       └─ theme/Theme.kt
     └─ res/values/strings.xml
```

## Notes
- No cloud backup (local only)
- No categories management UI (just text input)
- No export/import yet

## License
Free to use and modify.
