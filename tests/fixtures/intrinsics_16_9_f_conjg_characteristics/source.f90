program i169f_conjg_characteristics
  implicit none
  complex(kind=kind(0.0d0)) :: scalar_z, vector_z(2)
  scalar_z = cmplx(2.0d0, 3.0d0, kind=kind(0.0d0))
  vector_z = [cmplx(2.0d0, 3.0d0, kind=kind(0.0d0)), cmplx(-4.0d0, -5.0d0, kind=kind(0.0d0))]
  call require_true('conjg scalar result kind direct', kind(conjg(scalar_z)) == kind(scalar_z))
  call require_true('conjg vector result kind direct', kind(conjg(vector_z)) == kind(vector_z))
  call require_true('conjg direct shape inquiry', all(shape(conjg(vector_z)) == shape(vector_z)))
  write(*,'(a)') 'INTRINSICS 16.9.F CONJG CHARACTERISTICS OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169f_conjg_characteristics
