program data_statement_r846_repeats
  implicit none
  integer :: a(3)
  data a /43, 2*47/
  if (a(1) /= 43) error stop 1
  if (a(2) /= 47) error stop 2
  if (a(3) /= 47) error stop 3
  write(*,'(a)') 'DATA STATEMENT R846 REPEATS OK'
end program data_statement_r846_repeats
