program expr_overall_recursive_primary
  implicit none
  integer :: checks, primary_value
  checks=0
  if (((1+2)*3) /= 9) error stop 'EOR:recursive'
  checks=checks+1
  primary_value = 6
  if (primary_value + 4 /= 10) error stop 'EOR:primary-add'
  if (.not. (primary_value == 6)) error stop 'EOR:primary-relation'
  checks=checks+1
  if (checks /= 2) error stop 'EOR:checks'
  write(*,'(a)') 'EXPRESSIONS OVERALL RECURSIVE PRIMARY OK'
end program expr_overall_recursive_primary
