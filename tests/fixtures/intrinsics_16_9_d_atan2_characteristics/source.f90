program i169d_atan2_characteristics
  implicit none
  integer, parameter :: RK = kind(0.0d0)
  real(kind=RK) :: y(2), x(2)
  y = [1.0_RK, -1.0_RK]
  x = [2.0_RK, 2.0_RK]
  associate(result => atan2(y, x))
    call require_true('atan2 result kind same as x', kind(result) == kind(x))
    call require_true('atan2 result rank same as x', rank(result) == rank(x))
    call require_true('atan2 result extent same as x', size(result) == size(x))
  end associate
  write(*,'(a)') 'INTRINSICS 16.9.D ATAN2 CHARACTERISTICS OK'
contains
  subroutine require_true(label, condition)
    character(len=*), intent(in) :: label
    logical, intent(in) :: condition
    if (.not. condition) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
  subroutine require_complex_kind(label, value)
    character(len=*), intent(in) :: label
    complex(kind=kind(0.0d0)), intent(in) :: value
    call require_true(label, kind(value) == kind(0.0d0))
  end subroutine require_complex_kind
end program i169d_atan2_characteristics
