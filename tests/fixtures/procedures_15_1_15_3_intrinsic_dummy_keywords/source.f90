! rule: S15.1-003
! covers: see fixture.json facets
! evidence: effect
! standard: f2023
program intrinsic_dummy_keywords
  implicit none
  integer :: value
  value = -777
  value = abs(a=-42)
  if (value /= 42) error stop 1
  value = -778
  value = index(substring='42', string='ab42')
  if (value /= 3) error stop 2
  print '(a)', 'PROCEDURES 15.1 INTRINSIC DUMMY KEYWORDS OK'
end program
