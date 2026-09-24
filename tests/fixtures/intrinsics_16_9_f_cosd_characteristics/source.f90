program i169f_cosd_characteristics
  implicit none
  real(kind=kind(0.0d0)) :: x(2)
  x = [0.0d0, 60.0d0]
  call require_true('cosd result kind direct', kind(cosd(x)) == kind(x))
  call require_true('cosd direct shape inquiry', all(shape(cosd(x)) == shape(x)))
  write(*,'(a)') 'INTRINSICS 16.9.F COSD CHARACTERISTICS OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169f_cosd_characteristics
