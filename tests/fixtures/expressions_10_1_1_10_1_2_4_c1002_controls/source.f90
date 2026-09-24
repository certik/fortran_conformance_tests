program expr_c1002_controls
  implicit none
  integer :: checks, local_array(3), actual(3)
  checks=0
  local_array = [4,5,6]
  if (any(local_array /= [4,5,6])) error stop 'EC1002:ordinary'
  checks=checks+1
  actual = [10,20,30]
  call observe(actual)
  checks=checks+1
  if (checks /= 2) error stop 'EC1002:checks'
  write(*,'(a)') 'EXPRESSIONS C1002 CONTROLS OK'
contains
  subroutine observe(a)
    integer, intent(in) :: a(*)
    if (a(1) /= 10) error stop 'EC1002:element'
  end subroutine observe
end program expr_c1002_controls
