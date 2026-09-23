program pointer_assignment_syntax_remap
  implicit none
  integer, target :: v(-3:2), alt(-3:2)
  integer, pointer :: p(:,:)
  integer :: checks
  checks = 0
  v(-3) = 101
  v(-2) = 102
  v(-1) = 103
  v(0) = 104
  v(1) = 105
  v(2) = 106
  alt(-3) = -900
  alt(-2) = -900
  alt(-1) = -900
  alt(0) = -900
  alt(1) = -900
  alt(2) = -900
  p(-1:0,4:6) => v
  if (any(lbound(p) /= [-1,4])) error stop 201
  checks = checks + 1
  if (any(ubound(p) /= [0,6])) error stop 202
  checks = checks + 1
  if (any(shape(p) /= [2,3])) error stop 203
  checks = checks + 1
  p(0,6) = 961
  if (v(2) /= 961) error stop 204
  checks = checks + 1
  v(-1) = 862
  if (p(-1,5) /= 862) error stop 205
  checks = checks + 1
  if (alt(2) /= -900) error stop 206
  checks = checks + 1
  if (checks /= 6) error stop 207
  write(*,'(a)') 'pointer_assignment_syntax_remap OK'
end program pointer_assignment_syntax_remap
