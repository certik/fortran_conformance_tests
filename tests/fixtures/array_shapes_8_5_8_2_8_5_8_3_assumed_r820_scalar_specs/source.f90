program assumed_r820_scalar_specs
  implicit none
  integer :: actual(-2:0)
  actual=17
  call omitted(actual)
  call specified(actual)
  write(*,'(a)') 'ARRAY SHAPES R820 OK'
contains
  subroutine omitted(x)
    integer, intent(in) :: x(:)
    if (any(lbound(x) /= [1])) error stop 'R820 omitted lower'
  end subroutine omitted
  subroutine specified(x)
    integer, intent(in) :: x(-3:)
    if (any(lbound(x) /= [-3])) error stop 'R820 specified lower'
  end subroutine specified
end program assumed_r820_scalar_specs
