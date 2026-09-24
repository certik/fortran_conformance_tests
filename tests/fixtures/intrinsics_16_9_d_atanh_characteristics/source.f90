program i169d_atanh_characteristics
  implicit none
  integer, parameter :: RK = kind(0.0d0)
  real(kind=RK) :: real_x(2)
  complex(kind=RK) :: complex_x
  real_x = [-0.25_RK, 0.25_RK]
  complex_x = cmplx(0.0_RK, 0.5_RK, kind=RK)
  associate(real_result => atanh(real_x))
    call require_true('atanh real result kind same as x', kind(real_result) == kind(real_x))
    call require_true('atanh real result extent same as x', size(real_result) == size(real_x))
  end associate
  call require_true('atanh complex expression kind same as x', kind(atanh(complex_x)) == kind(complex_x))
  call require_complex_kind('atanh complex expression type discriminator', atanh(complex_x))
  write(*,'(a)') 'INTRINSICS 16.9.D ATANH CHARACTERISTICS OK'
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
end program i169d_atanh_characteristics
