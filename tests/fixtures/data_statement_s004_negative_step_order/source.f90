program data_statement_s004_negative_step_order
  implicit none
  integer :: a(3)
  integer :: i
  data (a(i), i=3,1,-1) /31, 21, 11/
  if (a(3) /= 31) error stop 1
  if (a(2) /= 21) error stop 2
  if (a(1) /= 11) error stop 3
  write(*,'(a)') 'DATA STATEMENT S004 NEGATIVE STEP ORDER OK'
end program data_statement_s004_negative_step_order
