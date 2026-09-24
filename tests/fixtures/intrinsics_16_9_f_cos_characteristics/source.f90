program i169f_cos_characteristics
  implicit none
  real(kind=kind(0.0d0)) :: real_x(2)
  complex(kind=kind(0.0d0)) :: complex_x(2)
  real_x = [0.0d0, 1.0d0]
  complex_x = [cmplx(0.0d0, 0.0d0, kind=kind(0.0d0)), cmplx(1.0d0, 0.0d0, kind=kind(0.0d0))]
  call require_true('cos real result kind direct', kind(cos(real_x)) == kind(real_x))
  call require_true('cos direct shape inquiry', all(shape(cos(real_x)) == shape(real_x)))
  call require_true('cos complex result kind direct', kind(cos(complex_x)) == kind(complex_x))
  call require_true('cos complex direct shape inquiry', all(shape(cos(complex_x)) == shape(complex_x)))
  write(*,'(a)') 'INTRINSICS 16.9.F COS CHARACTERISTICS OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169f_cos_characteristics
