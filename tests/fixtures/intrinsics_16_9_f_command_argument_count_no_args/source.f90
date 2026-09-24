program i169f_command_argument_count_kind
  implicit none
  integer, parameter :: WIDE = selected_int_kind(18)
  integer :: observed_kind
  observed_kind = -777
  observed_kind = kind(command_argument_count())
  call require_true('command_argument_count default integer kind', observed_kind == kind(0))
  write(*,'(a)') 'INTRINSICS 16.9.F COMMAND ARGUMENT COUNT NO ARGS OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169f_command_argument_count_kind
