! rule: C1548
! covers: nonpointer-discontiguous-dummy-no-contiguous
! evidence: effect
! standard: f2023
program c1548_volatile_control
  implicit none
  integer, volatile :: a(3) = [10, 20, 30]
  integer :: seen(2) = [-1, -2]
  call observe(a(3:1:-2), seen)
  call expect_vector2(seen, [30,10], 'volatile nonpointer discontiguous values')
  write(*,'(a)') 'C1548 CONTIGUOUS CONTROL OK'
contains
  subroutine observe(x, seen)
    integer, volatile :: x(:)
    integer, intent(out) :: seen(2)
    seen = x
  end subroutine
  subroutine expect_vector2(got, want, label)
    integer, intent(in) :: got(2), want(2)
    character(len=*), intent(in) :: label
    if (any(got /= want)) error stop label
  end subroutine
end program
