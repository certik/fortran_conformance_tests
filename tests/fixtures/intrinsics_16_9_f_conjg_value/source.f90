program i169f_conjg_value
  implicit none
  complex(kind=kind(0.0d0)) :: z(2), result(2)
  z = [cmplx(2.0d0, 3.0d0, kind=kind(0.0d0)), cmplx(-4.0d0, -5.0d0, kind=kind(0.0d0))]
  result = cmplx(-77.0d0, 88.0d0, kind=kind(0.0d0))
  result = conjg(z)
  call require_true('conjg real parts unchanged', all(real(result) == [2.0d0, -4.0d0]))
  call require_true('conjg imaginary parts negated', all(aimag(result) == [-3.0d0, 5.0d0]))
  write(*,'(a)') 'INTRINSICS 16.9.F CONJG VALUE OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169f_conjg_value
