// Harvard-style one-column resume. Data arrives as JSON in sys.inputs.resume.
#let r = json(bytes(sys.inputs.resume))
#let get(d, key, default: none) = d.at(key, default: default)

#set page(paper: "us-letter", margin: (x: 0.6in, y: 0.5in))
#set text(font: "Libertinus Serif", size: 10.5pt)
#set par(justify: false, spacing: 0.5em)
#set list(indent: 0.8em, spacing: 0.4em)

#let heading-line(title) = {
  v(1.2em, weak: true)
  text(weight: "bold", smallcaps(title))
  v(-0.1em)
  line(length: 100%, stroke: 0.5pt)
  v(0.2em)
}

// Left text, right text on the same line.
#let split(left, right) = {
  if right == none or right == "" { left } else { left + h(1fr) + right }
}

#let bullets(items) = {
  if items != none and items.len() > 0 { list(..items) }
}

#let nonempty(x) = x != none and x.len() > 0

// Header
#let c = r.contact
#align(center)[
  #text(size: 18pt, weight: "bold", c.name)
  #let headline = get(r, "headline")
  #if headline != none and headline != "" [
    \ #text(size: 11pt, style: "italic", headline)
  ]
  #let parts = (get(c, "location"), get(c, "email"), get(c, "phone"))
  #let parts = (parts + get(c, "links", default: ())).filter(p => p != none and p != "")
  #if parts.len() > 0 [
    \ #parts.join("  |  ")
  ]
]

// Experience
#let experience = get(r, "experience", default: ())
#if nonempty(experience) {
  heading-line("Experience")
  for job in experience {
    block(breakable: false, above: 0.8em, below: 0pt)[
      #split(strong(job.company), get(job, "location"))
      #for role in get(job, "roles", default: ()) {
        v(0.15em)
        split(emph(role.title), get(role, "dates"))
        bullets(get(role, "bullets", default: ()))
      }
    ]
  }
}

// Projects
#let projects = get(r, "projects", default: ())
#if nonempty(projects) {
  heading-line("Projects")
  for p in projects {
    block(breakable: false, above: 0.8em, below: 0pt)[
      #split(strong(p.name), get(p, "dates"))
      #bullets(get(p, "bullets", default: ()))
    ]
  }
}

// Leadership
#let leadership = get(r, "leadership", default: ())
#if nonempty(leadership) {
  heading-line("Leadership")
  for l in leadership {
    block(breakable: false, above: 0.8em, below: 0pt)[
      #split(strong(l.organization), get(l, "dates"))
      #if get(l, "role") != none { parbreak(); emph(l.role) }
      #bullets(get(l, "bullets", default: ()))
    ]
  }
}

// Education
#let education = get(r, "education", default: ())
#if nonempty(education) {
  heading-line("Education")
  for e in education {
    block(breakable: false, above: 0.8em, below: 0pt)[
      #split(strong(e.school), get(e, "location")) \
      #split(emph(e.degree), get(e, "dates"))
      #bullets(get(e, "details", default: ()))
    ]
  }
}

// Skills
#let skills = get(r, "skills", default: ())
#let certs = get(r, "certifications", default: ())
#if nonempty(skills) or nonempty(certs) {
  heading-line("Skills")
  for s in skills [
    #strong(s.category + ":") #s.items.join(", ") \
  ]
  if nonempty(certs) [
    #strong("Certifications:") #certs.join(", ")
  ]
}
