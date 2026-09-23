program data_statement_r840_sets
  implicit none
  integer :: single, comma_left, comma_right, bare_left, bare_right
  data single /17/
  data comma_left /19/, comma_right /23/
  data bare_left /29/ bare_right /31/
  if (single /= 17) error stop 1
  if (comma_left /= 19) error stop 2
  if (comma_right /= 23) error stop 3
  if (bare_left /= 29) error stop 4
  if (bare_right /= 31) error stop 5
  write(*,'(a)') 'DATA STATEMENT R840 SETS OK'
end program data_statement_r840_sets
