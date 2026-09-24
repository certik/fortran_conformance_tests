program i169f_count_description
  implicit none
  integer :: description_count
  description_count = -777
  description_count = count([.true., .false., .true.])
  call require_true('count true value reduction description', description_count == 2)
  write(*,'(a)') 'INTRINSICS 16.9.F COUNT DESCRIPTION TRANSFORM OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169f_count_description
