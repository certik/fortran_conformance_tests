program i169d_atanh_elemental
  implicit none
  real :: x(3)
  x = [-0.5, 0.0, 0.5]
  associate(observed => atanh(x))
    call require_true('atanh elemental rank one result', rank(observed) == 1)
    call require_true('atanh elemental extent follows argument', size(observed) == 3)
  end associate
  write(*,'(a)') 'INTRINSICS 16.9.D ATANH ELEMENTAL OK'
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
end program i169d_atanh_elemental
