const API_BASE = "http://127.0.0.1:8000";

// تغییر فیلدهای فرم بر اساس نقش کاربر
function toggleRoleFields() {
    const role = document.getElementById("roleSelect").value;
    const input = document.getElementById("usernameInput");

    if (input) {
        if (role === "parent") {
            input.placeholder = "شناسه دانش‌آموز (Student ID)";
        } else {
            input.placeholder = "نام کاربری";
        }
    }
}

// مدیریت لاگین
const loginForm = document.getElementById("loginForm");
if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const role = document.getElementById("roleSelect").value;
        const usernameVal = document.getElementById("usernameInput").value;
        const passwordVal = document.getElementById("passwordInput").value;
        const errorAlert = document.getElementById("errorAlert");

        let endpoint = "";
        let bodyData = {};

        if (role === "admin") {
            endpoint = "/auth/admin/login";
            bodyData = { username: usernameVal, password: passwordVal };
        } else if (role === "teacher") {
            endpoint = "/auth/teacher/login";
            bodyData = { username: usernameVal, password: passwordVal };
        } else if (role === "parent") {
            endpoint = "/auth/parent/login";
            bodyData = { student_id: parseInt(usernameVal), password: passwordVal };
        }

        try {
            const res = await fetch(API_BASE + endpoint, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(bodyData)
            });

            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.detail || "اطلاعات ورود نادرست است");
            }

            localStorage.setItem("token", data.access_token);
            localStorage.setItem("role", role);

            // هدایت خودکار بر اساس نقش کاربر به پنل‌های مربوطه
            if (role === "admin") {
                window.location.href = "/admin-panel";
            } else if (role === "teacher") {
                window.location.href = "/teacher-panel";
            } else if (role === "parent") {
                window.location.href = "/parent-panel";
            }
        } catch (err) {
            if (errorAlert) {
                errorAlert.innerText = err.message;
                errorAlert.style.display = "block";
            }
        }
    });
}

// بارگذاری لیست دبیران در پنل مدیریت
async function loadTeachers() {
    const token = localStorage.getItem("token");
    if (!token) {
        window.location.href = "/";
        return;
    }

    try {
        const res = await fetch(API_BASE + "/manage/teachers", {
            headers: { "Authorization": `Bearer ${token}` }
        });

        if (!res.ok) {
            throw new Error("دسترسی غیرمجاز");
        }

        const teachers = await res.json();
        const tbody = document.getElementById("teachersTableBody");

        if (tbody) {
            tbody.innerHTML = teachers.map(t => `
                <tr>
                    <td>${t.id}</td>
                    <td>${t.name}</td>
                    <td>${t.subject}</td>
                    <td>${t.class_name}</td>
                    <td>${t.username}</td>
                </tr>
            `).join('');
        }
    } catch (err) {
        console.error("خطا در دریافت لیست دبیران:", err);
    }
}

// ثبت دبیر جدید
const createTeacherForm = document.getElementById("createTeacherForm");
if (createTeacherForm) {
    createTeacherForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const token = localStorage.getItem("token");

        const payload = {
            name: document.getElementById("tName").value,
            subject: document.getElementById("tSubject").value,
            class_name: document.getElementById("tClass").value,
            username: document.getElementById("tUsername").value,
            password: document.getElementById("tPassword").value
        };

        try {
            const res = await fetch(API_BASE + "/manage/teachers", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                alert("دبیر با موفقیت ثبت شد");
                createTeacherForm.reset();
                loadTeachers();
            } else {
                const err = await res.json();
                alert("خطا: " + err.detail);
            }
        } catch (err) {
            alert("خطا در برقراری ارتباط با سرور");
        }
    });
}

function logout() {
    localStorage.clear();
    window.location.href = "/";
}

// ثبت حضور و غیاب
async function submitAttendance() {
    const studentId = document.getElementById("attendance-student-id").value;
    const date = document.getElementById("attendance-date").value;
    const status = document.getElementById("attendance-status").value;

    try {
        const response = await fetch(API_BASE + "/manage/attendance", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + localStorage.getItem("token")
            },
            body: JSON.stringify({
                student_id: parseInt(studentId),
                date: date,
                status: status
            })
        });

        if (response.ok) {
            alert("حضور و غیاب با موفقیت ثبت شد");
        } else {
            const err = await response.json();
            console.error(err);
            alert("خطا: " + (err.detail || "ثبت انجام نشد"));
        }
    } catch (err) {
        console.error("خطا در ارتباط با سرور:", err);
        alert("خطا در ارتباط با سرور");
    }
}

// ثبت نمره
async function submitGrade() {
    const studentId = document.getElementById("grade-student-id").value;
    const subject = document.getElementById("grade-subject").value;
    const score = document.getElementById("grade-value").value;
    const date = document.getElementById("grade-date").value;

    try {
        const response = await fetch(API_BASE + "/teacher/grades", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + localStorage.getItem("token")
            },
            body: JSON.stringify({
                student_id: parseInt(studentId),
                subject: subject,
                score: parseFloat(score),
                date: date
            })
        });

        if (response.ok) {
            alert("نمره با موفقیت ثبت شد");
        } else {
            const err = await response.json();
            alert("خطا: " + (err.detail || "ثبت نمره انجام نشد"));
        }
    } catch (err) {
        console.error("خطا در ارتباط با سرور:", err);
        alert("خطا در ارتباط با سرور");
    }
}

// ارسال گزارش ماهانه برای اولیا (وضعیت اولیه: pending)
async function submitMonthlyReport() {
    const studentId = document.getElementById("report-student-id").value;
    const month = document.getElementById("report-month").value;
    const academic = document.getElementById("report-academic").value;
    const disciplinary = document.getElementById("report-disciplinary").value;

    try {
        const response = await fetch(API_BASE + "/teacher/reports", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + localStorage.getItem("token")
            },
            body: JSON.stringify({
                student_id: parseInt(studentId),
                month: month,
                academic_status: academic,
                disciplinary_status: disciplinary
            })
        });

        if (response.ok) {
            alert("گزارش با موفقیت ثبت شد و در انتظار تأیید مدیر است");
        } else {
            const err = await response.json();
            alert("خطا: " + (err.detail || "ثبت گزارش انجام نشد"));
        }
    } catch (err) {
        console.error("خطا در ارتباط با سرور:", err);
        alert("خطا در ارتباط با سرور");
    }
}
// هماهنگی توکن بین دو سیستم لاگین
if (!localStorage.getItem("token") && localStorage.getItem("school_ai_token")) {
    localStorage.setItem("token", localStorage.getItem("school_ai_token"));
}