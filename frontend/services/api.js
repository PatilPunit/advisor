const API_URL = "http://127.0.0.1:7000";

export async function getRecommendation(data) {
    const response = await fetch(
        `${API_URL}/recommend`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        }
    );

    return await response.json();
}