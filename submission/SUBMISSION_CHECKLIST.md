# Challenge Submission Checklist

## Needs team-leader input

- [ ] Replace `TEAM_NAME_COLLEGE_NAME` with the official team and college folder name.
- [ ] Add team member roles and college/incubator to the root README.
- [ ] Record and link a public or unlisted video of at least 20 minutes.
- [ ] Add the team leader's name, phone, email, and public repository URL only to the
  official submission platform unless the organizers explicitly require them in Git.

## Technical evidence

- [x] Static synthetic EHR is present.
- [x] Dynamic synthetic CGM flows through MQTT.
- [x] Spring Boot fuses both streams into one digital-twin response.
- [x] FastAPI returns a real versioned model prediction or an explicit unavailable state.
- [x] React presents the virtual patient to a clinician.
- [x] Raw patient-level research data is excluded from the public repository.
- [x] Open-source licence is present.
- [x] Architecture PDF/PPT and presentation PDF/PPT are exported and visually checked.
- [ ] Clinical reviewer signs off visible language and limitations.

## Final public-repository check

- [ ] Repository visibility is Public.
- [ ] All README links open without authentication.
- [ ] Fresh `docker compose up --build` succeeds on another computer.
- [ ] Demo video link works in an incognito/private browser window.
- [ ] No secrets, personal health data, `.env`, or raw restricted datasets are tracked.
