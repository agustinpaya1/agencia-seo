"use server";

import { revalidateTag } from "next/cache";

export async function startAuditAction(prevState: any, formData: FormData) {
  const url = formData.get("url") as string;

  if (!url || url.trim() === "") {
    return { error: "La URL es obligatoria" };
  }

  try {
    const response = await fetch("http://127.0.0.1:8000/api/audit", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url: url.trim() }),
    });

    if (response.ok) {
      revalidateTag("prospects");
      return { success: true, message: "Auditoría iniciada correctamente" };
    } else {
      return { error: "Falló la conexión con el motor de auditoría" };
    }
  } catch (error) {
    return { error: "Error al comunicarse con el servidor de auditoría" };
  }
}
