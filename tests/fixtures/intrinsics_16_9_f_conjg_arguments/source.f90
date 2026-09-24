program i169f_conjg_arguments
  implicit none
  complex(kind=kind(0.0d0)) :: scalar_z, scalar_result
  complex(kind=kind(0.0d0)) :: vector_z(2), vector_result(2)
  scalar_z = cmplx(2.0d0, 3.0d0, kind=kind(0.0d0))
  vector_z = [cmplx(2.0d0, 3.0d0, kind=kind(0.0d0)), cmplx(-4.0d0, -5.0d0, kind=kind(0.0d0))]
  scalar_result = cmplx(-77.0d0, 88.0d0, kind=kind(0.0d0))
  vector_result = cmplx(-77.0d0, 88.0d0, kind=kind(0.0d0))
  scalar_result = conjg(scalar_z)
  vector_result = conjg(vector_z)
  call require_true('conjg scalar complex argument reached', aimag(scalar_result) == -3.0d0)
  call require_true('conjg vector complex argument reached', all(aimag(vector_result) == [-3.0d0, 5.0d0]))
  write(*,'(a)') 'INTRINSICS 16.9.F CONJG ARGUMENTS OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169f_conjg_arguments
