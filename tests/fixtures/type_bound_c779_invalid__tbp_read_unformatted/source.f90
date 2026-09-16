module tbp_defs
implicit none
type :: record
contains
procedure, nopass :: io => io_impl
generic :: read(unformatted) => io
end type record
contains
subroutine io_impl(dtv,unit,iostat,iomsg)
class(record), intent(inout) :: dtv
integer, intent(in) :: unit
integer, intent(out) :: iostat
character(*), intent(inout) :: iomsg
iostat = 0
end subroutine io_impl
end module tbp_defs
