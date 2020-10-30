create database IF NOT EXISTS ga;
use ga;

create table IF NOT EXISTS Object (
	created_at timestamp not null default current_timestamp,
	updated_at timestamp not null default current_timestamp on update current_timestamp,
	ObjectID bigint unsigned not null auto_increment,
	ObjectName varchar(255) not null,
	ObjectDescription varchar(255) null default null,
	primary key (ObjectID)
)engine innodb,
 character set utf8,
 collate utf8_unicode_ci;

create table IF NOT EXISTS SettingValueType (
	created_at timestamp not null default current_timestamp,
	updated_at timestamp not null default current_timestamp on update current_timestamp,
	ValueID bigint unsigned not null auto_increment,
	ValueName varchar(255) not null,
	ValueUnit varchar(255) not null,
	ValueDescription varchar(255) null default null,
	primary key (ValueID)
)engine innodb,
 character set utf8,
 collate utf8_unicode_ci;

create table IF NOT EXISTS SettingType (
	created_at timestamp not null default current_timestamp,
	updated_at timestamp not null default current_timestamp on update current_timestamp,
	TypeID bigint unsigned not null auto_increment,
	TypeKey varchar(255) not null,
	TypeDescription varchar(255) null default null,
	TypeValueID bigint unsigned not null,
	primary key (TypeID),
	foreign key st_fk_typevalueid (TypeValueID) references SettingValueType (ValueID) on update cascade on delete cascade
)engine innodb,
 character set utf8,
 collate utf8_unicode_ci;

create table IF NOT EXISTS ObjectSetting (
	created_at timestamp not null default current_timestamp,
	updated_at timestamp not null default current_timestamp on update current_timestamp,
	SettingID bigint unsigned not null auto_increment,
	ObjectID bigint unsigned null default null,
	SettingTypeID bigint unsigned not null,
	SettingValue varchar(255),
	primary key (SettingID),
	foreign key os_fk_objectid (ObjectID) references Object (ObjectID) on update cascade on delete cascade,
	foreign key os_fk_settingtypeid (SettingTypeID) references SettingType (TypeID) on update cascade on delete cascade,
    unique key os_uk_settingtypeid_objectid (SettingTypeID, ObjectID)
)engine innodb,
 character set utf8,
 collate utf8_unicode_ci;

create table IF NOT EXISTS GrpType (
	created_at timestamp not null default current_timestamp,
	updated_at timestamp not null default current_timestamp on update current_timestamp,
	TypeID bigint unsigned not null auto_increment,
	TypeName varchar(255) not null,
	TypeCategory varchar(255) not null,
	TypeDescription varchar(255) null default null,
	primary key (TypeID)
)engine innodb,
 character set utf8,
 collate utf8_unicode_ci;

create table IF NOT EXISTS Grp (
	created_at timestamp not null default current_timestamp,
	updated_at timestamp not null default current_timestamp on update current_timestamp,
	GroupID bigint unsigned not null auto_increment,
	GroupName varchar(255) not null,
	GroupParent bigint unsigned null default null,
	GroupDescription varchar(255) null default null,
	GroupTypeID bigint unsigned null default null,
	primary key (GroupID),
	foreign key g_fk_grouptypeid (GroupTypeID) references GrpType (TypeID) on update cascade on delete cascade
)engine innodb,
 character set utf8,
 collate utf8_unicode_ci;

create table IF NOT EXISTS GrpSetting (
	created_at timestamp not null default current_timestamp,
	updated_at timestamp not null default current_timestamp on update current_timestamp,
	SettingID bigint unsigned not null auto_increment,
	GroupID bigint unsigned not null,
	SettingTypeID bigint unsigned not null,
	SettingValue varchar(255),
	primary key (SettingID),
	foreign key gs_fk_grpid (GroupID) references Grp (GroupID) on update cascade on delete cascade,
	foreign key gs_fk_settingtypeid (SettingTypeID) references SettingType (TypeID) on update cascade on delete cascade,
    unique key gs_uk_settingtypeid_groupid (SettingTypeID, GroupID)
)engine innodb,
 character set utf8,
 collate utf8_unicode_ci;

create table IF NOT EXISTS SettingGroupMember (
	created_at timestamp not null default current_timestamp,
	updated_at timestamp not null default current_timestamp on update current_timestamp,
	ChainID bigint unsigned not null auto_increment,
	GroupID bigint unsigned not null,
	SettingID bigint unsigned not null,
	primary key (ChainID),
	foreign key sgm_fk_settingid (SettingID) references ObjectSetting (SettingID) on update cascade on delete cascade,
	foreign key sgm_fk_groupid (GroupID) references Grp (GroupID) on update cascade on delete cascade,
	unique key sgm_uk_settingid_groupid (SettingID, GroupID)
)engine innodb,
 character set utf8,
 collate utf8_unicode_ci;

create table IF NOT EXISTS ObjectGroupMember (
	created_at timestamp not null default current_timestamp,
	updated_at timestamp not null default current_timestamp on update current_timestamp,
	ChainID bigint unsigned not null auto_increment,
	GroupID bigint unsigned not null,
	ObjectID bigint unsigned not null,
	primary key (ChainID),
	foreign key ogm_fk_objectid (ObjectID) references Object (ObjectID) on update cascade on delete cascade,
	foreign key ogm_fk_groupid (GroupID) references Grp (GroupID) on update cascade on delete cascade,
	unique key ogm_uk_objectid_groupid (ObjectID, GroupID)
)engine innodb,
 character set utf8,
 collate utf8_unicode_ci;

# data table
#   source, value

# task table
#   result, category, taskname, objectid, message (error/success msg)