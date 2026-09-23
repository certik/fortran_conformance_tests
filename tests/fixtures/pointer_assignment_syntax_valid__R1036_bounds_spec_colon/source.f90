program pointer_assignment_syntax_bounds_spec
  implicit none
  integer, target :: t(2:4,10:11), other(2:4,10:11)
  integer, pointer :: p(:,:)
  integer :: checks
  checks = 0
  t(2,10) = 201
  t(3,10) = 301
  t(4,10) = 401
  t(2,11) = 202
  t(3,11) = 302
  t(4,11) = 402
  other(2,10) = -700
  other(3,10) = -700
  other(4,10) = -700
  other(2,11) = -700
  other(3,11) = -700
  other(4,11) = -700
  p(-4:,6:) => t
  if (any(lbound(p) /= [-4,6])) error stop 101
  checks = checks + 1
  if (any(ubound(p) /= [-2,7])) error stop 102
  checks = checks + 1
  if (any(shape(p) /= [3,2])) error stop 103
  checks = checks + 1
  p(-4,6) = 741
  if (t(2,10) /= 741) error stop 104
  checks = checks + 1
  t(3,11) = 852
  if (p(-3,7) /= 852) error stop 105
  checks = checks + 1
  if (other(2,10) /= -700) error stop 106
  checks = checks + 1
  if (checks /= 6) error stop 107
  write(*,'(a)') 'pointer_assignment_syntax_bounds_spec OK'
end program pointer_assignment_syntax_bounds_spec
