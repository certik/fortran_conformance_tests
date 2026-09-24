module expr_category_unary_m
  implicit none
  interface operator(.u.)
    module procedure u
  end interface
contains
  integer function u(x)
    integer, intent(in) :: x
    u = 10*x
  end function u
end module expr_category_unary_m
program expr_overall_categories
  use expr_category_unary_m
  implicit none
  integer :: checks
  character(len=4) :: word
  checks=0
  if (6 /= 6) error stop 'EOC:primary'
  checks=checks+1
  if (.u. 5 /= 50) error stop 'EOC:level1'
  checks=checks+1
  if (2**3 /= 8) error stop 'EOC:level2'
  checks=checks+1
  word = 'ab'//'cd'
  if (len(word) /= 4) error stop 'EOC:level3-len'
  if (word /= 'abcd') error stop 'EOC:level3'
  checks=checks+1
  if (.not. (9 > 4)) error stop 'EOC:level4'
  checks=checks+1
  if (.not. (.true. .and. .true.)) error stop 'EOC:level5'
  checks=checks+1
  if (checks /= 6) error stop 'EOC:checks'
  write(*,'(a)') 'EXPRESSIONS OVERALL CATEGORIES OK'
end program expr_overall_categories
