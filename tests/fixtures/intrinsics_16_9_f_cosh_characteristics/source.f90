program i169f_cosh_characteristics
  implicit none
  real(kind=kind(0.0d0)) :: real_x(2)
  complex(kind=kind(0.0d0)) :: complex_x(2)
  real_x = [0.0d0, 1.0d0]
  complex_x = [cmplx(0.0d0, 0.0d0, kind=kind(0.0d0)), cmplx(0.0d0, 1.0d0, kind=kind(0.0d0))]
  call require_true('cosh real result kind direct', kind(cosh(real_x)) == kind(real_x))
  call require_true('cosh real direct shape inquiry', all(shape(cosh(real_x)) == shape(real_x)))
  call require_true('cosh complex result kind direct', kind(cosh(complex_x)) == kind(complex_x))
  call require_true('cosh direct shape inquiry', all(shape(cosh(complex_x)) == shape(complex_x)))
  write(*,'(a)') 'INTRINSICS 16.9.F COSH CHARACTERISTICS OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169f_cosh_characteristics
