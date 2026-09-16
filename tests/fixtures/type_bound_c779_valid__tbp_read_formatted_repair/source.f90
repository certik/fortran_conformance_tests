module tbp_defs
implicit none
type :: record
contains
procedure :: io => io_impl
generic :: read(formatted) => io
end type record
contains
subroutine io_impl(dtv,unit,iotype,v_list,iostat,iomsg)
class(record), intent(inout) :: dtv
integer, intent(in) :: unit
character(*), intent(in) :: iotype
integer, intent(in) :: v_list(:)
integer, intent(out) :: iostat
character(*), intent(inout) :: iomsg
iostat = 0
end subroutine io_impl
end module tbp_defs
