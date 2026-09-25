program assumed_s002_scalar_lowers
  implicit none
  integer :: actual(-2:0,4:5)
  actual=31
  call omitted(actual)
  call specified(actual)
  call mixed(actual)
  write(*,'(a)') 'ARRAY SHAPES ASSUMED S002 LOWERS OK'
contains
  subroutine omitted(x)
    integer, intent(in) :: x(:,:)
    if (any(lbound(x) /= [1,1])) error stop 'S002 omitted lower'
    if (any(ubound(x) /= [3,2])) error stop 'S002 omitted upper'
  end subroutine omitted
  subroutine specified(x)
    integer, intent(in) :: x(0:,-3:)
    if (any(lbound(x) /= [0,-3])) error stop 'S002 specified lower'
    if (any(ubound(x) /= [2,-2])) error stop 'S002 specified upper'
  end subroutine specified
  subroutine mixed(x)
    integer, intent(in) :: x(0:,:)
    if (any(lbound(x) /= [0,1])) error stop 'S002 mixed lower'
    if (any(ubound(x) /= [2,2])) error stop 'S002 mixed upper'
  end subroutine mixed
end program assumed_s002_scalar_lowers
