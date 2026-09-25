program assumed_s002_empty_inquiry
  implicit none
  integer :: empty(5:3,-2:1)
  call observe_empty(empty)
  write(*,'(a)') 'ARRAY SHAPES ASSUMED S002 EMPTY OK'
contains
  subroutine observe_empty(x)
    integer, intent(in) :: x(5:,-2:)
    if (any(lbound(x) /= [1,-2])) error stop 'S002 empty lbound'
    if (any(ubound(x) /= [0,1])) error stop 'S002 empty ubound'
  end subroutine observe_empty
end program assumed_s002_empty_inquiry
