program expr_c1004_rank_control
  implicit none
  integer :: checks, x
  checks=0
  x = (.true. ? 1 : 2)
  if (x /= 1) error stop 'EC1004:rank-control'
  checks=checks+1
  if (checks /= 1) error stop 'EC1004:checks'
  write(*,'(a)') 'EXPRESSIONS C1004 RANK CONTROL OK'
end program expr_c1004_rank_control
