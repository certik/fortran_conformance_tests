! rule: C1549
! covers: array-pointer-noncontiguous-dummy-no-contiguous
! evidence: effect
! standard: f2023
program c1549_volatile_control
  implicit none
  integer, target :: a(5) = [10, 20, 30, 40, 50]
  integer, pointer, volatile :: p(:)
  integer :: seen(3) = [-1, -2, -3]
  p => a(1:5:2)
  call observe(p, seen)
  call expect_vector3(seen, [10,30,50], 'volatile pointer discontiguous values')
  write(*,'(a)') 'C1549 CONTIGUOUS CONTROL OK'
contains
  subroutine observe(x, seen)
    integer, volatile :: x(:)
    integer, intent(out) :: seen(3)
    seen = x
  end subroutine
  subroutine expect_vector3(got, want, label)
    integer, intent(in) :: got(3), want(3)
    character(len=*), intent(in) :: label
    if (any(got /= want)) error stop label
  end subroutine
end program
