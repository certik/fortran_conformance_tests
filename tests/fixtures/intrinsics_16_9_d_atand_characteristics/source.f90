program i169d_atand_characteristics
  implicit none
  integer, parameter :: RK = kind(0.0d0)
  real(kind=RK) :: x(2)
  x = [-0.5_RK, 0.5_RK]
  associate(result => atand(x))
    call require_true('atand result kind same as x', kind(result) == kind(x))
    call require_true('atand result rank same as x', rank(result) == rank(x))
    call require_true('atand result extent same as x', size(result) == size(x))
  end associate
  write(*,'(a)') 'INTRINSICS 16.9.D ATAND CHARACTERISTICS OK'
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
end program i169d_atand_characteristics
