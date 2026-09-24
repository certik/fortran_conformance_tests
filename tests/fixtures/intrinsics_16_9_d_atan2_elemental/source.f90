program i169d_atan2_elemental
  implicit none
  real :: y(3), x(3)
  y = [1.0, 0.5, -1.0]
  x = [2.0, 2.0, 2.0]
  associate(observed => atan2(y, x))
    call require_true('atan2 elemental rank one result', rank(observed) == 1)
    call require_true('atan2 elemental extent follows arguments', size(observed) == 3)
  end associate
  write(*,'(a)') 'INTRINSICS 16.9.D ATAN2 ELEMENTAL OK'
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
end program i169d_atan2_elemental
